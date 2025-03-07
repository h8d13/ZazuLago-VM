#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define BUFFER_SIZE (32 * 1024 * 1024) // 32MB per thread buffer
#define MAX_THREADS 32
#define CACHE_LINE 64

// Align to cache line to prevent false sharing
typedef struct {
    uint8_t *buffer;
    size_t length;
    uint64_t magic_number;
    size_t thread_id;
    char padding[CACHE_LINE - sizeof(uint8_t*) - sizeof(size_t) - sizeof(uint64_t) - sizeof(size_t)];
} __attribute__((aligned(CACHE_LINE))) ThreadData;

// Process data in 128-bit chunks when possible (using two 64-bit operations)
void process_data(uint8_t *buffer, size_t length, uint64_t magic_number) {
    // Ensure buffer is aligned for optimal performance
    uintptr_t addr = (uintptr_t)buffer;
    size_t misalign = addr & 0x7;
    
    // Handle misaligned start
    for (size_t i = 0; i < misalign && i < length; i++) {
        buffer[i] ^= (uint8_t)(magic_number >> (8 * (i % 8)));
    }
    
    // Adjust buffer and length for aligned processing
    uint64_t *buffer64 = (uint64_t *)(buffer + misalign);
    size_t aligned_length = (length - misalign) & ~0x7;
    size_t length64 = aligned_length / 8;
    
    // Prefetch hint for large arrays
    #pragma GCC unroll 8
    for (size_t i = 0; i < length64; i++) {
        // Prefetch data ahead
        __builtin_prefetch(&buffer64[i + 16], 0, 0);
        
        // XOR with magic number
        buffer64[i] ^= magic_number;
        
        // Rotate bits (circular shift left by 3)
        buffer64[i] = (buffer64[i] << 3) | (buffer64[i] >> 61);
        
        // Apply bit mask with a different pattern
        buffer64[i] ^= (magic_number << 17) | (magic_number >> 47);
        
        // Update magic number for each block (avalanche effect)
        magic_number = ((magic_number * 0x5851F42D4C957F2DULL) + 0x14057B7EF767814FULL) & 0xFFFFFFFFFFFFFFFFULL;
    }
    
    // Handle remaining bytes
    size_t remaining_offset = misalign + aligned_length;
    for (size_t i = remaining_offset; i < length; i++) {
        buffer[i] ^= (uint8_t)(magic_number >> (8 * ((i - remaining_offset) % 8)));
    }
}

void* thread_process_data(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    
    // Generate a unique seed for this thread based on thread_id
    uint64_t thread_magic = data->magic_number ^ (data->thread_id * 0x123456789ABCDEFULL);
    
    // Pin thread to a specific CPU core if possible (thread affinity)
    #ifdef __linux__
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(data->thread_id % 32, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    #endif
    
    process_data(data->buffer, data->length, thread_magic);
    
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 4 || argc > 5) {
        fprintf(stderr, "Usage: %s <input_file> <output_file> <magic_number> [num_threads]\n", argv[0]);
        return 1;
    }
    
    const char *input_filename = argv[1];
    const char *output_filename = argv[2];
    uint64_t magic_number = strtoull(argv[3], NULL, 0);
    
    // Determine optimal number of threads (default to available cores)
    int num_threads = sysconf(_SC_NPROCESSORS_ONLN);
    if (argc == 5) {
        int requested_threads = atoi(argv[4]);
        if (requested_threads > 0) {
            num_threads = requested_threads;
        }
    }
    if (num_threads > MAX_THREADS) num_threads = MAX_THREADS;
    
    // Open input file
    int input_fd = open(input_filename, O_RDONLY);
    if (input_fd == -1) {
        perror("Failed to open input file");
        return 1;
    }
    
    // Get file size
    struct stat st;
    if (fstat(input_fd, &st) != 0) {
        perror("Failed to get file size");
        close(input_fd);
        return 1;
    }
    size_t file_size = st.st_size;
    
    // Adjust number of threads for small files
    if (file_size < num_threads * BUFFER_SIZE / 2) {
        num_threads = (file_size / BUFFER_SIZE) + 1;
    }
    
    // Use memory mapping for input file
    uint8_t *file_data = mmap(NULL, file_size, PROT_READ, MAP_SHARED, input_fd, 0);
    if (file_data == MAP_FAILED) {
        perror("Failed to memory map input file");
        close(input_fd);
        return 1;
    }
    
    // Create output file
    int output_fd = open(output_filename, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (output_fd == -1) {
        perror("Failed to open output file");
        munmap(file_data, file_size);
        close(input_fd);
        return 1;
    }
    
    // Set output file size
    if (ftruncate(output_fd, file_size) == -1) {
        perror("Failed to set output file size");
        close(output_fd);
        munmap(file_data, file_size);
        close(input_fd);
        return 1;
    }
    
    // Memory map output file
    uint8_t *output_data = mmap(NULL, file_size, PROT_READ | PROT_WRITE, MAP_SHARED, output_fd, 0);
    if (output_data == MAP_FAILED) {
        perror("Failed to memory map output file");
        close(output_fd);
        munmap(file_data, file_size);
        close(input_fd);
        return 1;
    }
    
    // Start timing
    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);
    
    // Allocate memory for thread data
    ThreadData *thread_data = aligned_alloc(CACHE_LINE, num_threads * sizeof(ThreadData));
    pthread_t *threads = malloc(num_threads * sizeof(pthread_t));
    
    if (!thread_data || !threads) {
        perror("Failed to allocate memory for thread data");
        free(threads);
        free(thread_data);
        munmap(output_data, file_size);
        close(output_fd);
        munmap(file_data, file_size);
        close(input_fd);
        return 1;
    }
    
    // Calculate chunk size per thread
    size_t chunk_size = (file_size + num_threads - 1) / num_threads;
    // Round up to a multiple of 64 bytes (cache line) for better alignment
    chunk_size = (chunk_size + 63) & ~63;
    
    // Create threads
    for (int i = 0; i < num_threads; i++) {
        size_t offset = i * chunk_size;
        size_t length = chunk_size;
        
        // Adjust length for last chunk
        if (offset + length > file_size) {
            length = file_size - offset;
        }
        
        // Skip creating thread if no data to process
        if (length == 0) continue;
        
        // Copy data to output buffer first
        memcpy(output_data + offset, file_data + offset, length);
        
        // Set up thread data
        thread_data[i].buffer = output_data + offset;
        thread_data[i].length = length;
        thread_data[i].magic_number = magic_number;
        thread_data[i].thread_id = i;
        
        int ret = pthread_create(&threads[i], NULL, thread_process_data, &thread_data[i]);
        if (ret != 0) {
            fprintf(stderr, "Failed to create thread %d\n", i);
            // Continue with fewer threads
            num_threads = i;
            break;
        }
    }
    
    // Wait for all threads to complete
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Ensure all data is written to disk
    msync(output_data, file_size, MS_SYNC);
    
    // Calculate and display performance metrics
    clock_gettime(CLOCK_MONOTONIC, &end_time);
    double elapsed_seconds = (end_time.tv_sec - start_time.tv_sec) + 
                             (end_time.tv_nsec - start_time.tv_nsec) / 1e9;
    double speed_mbps = (file_size / (1024.0 * 1024.0)) / elapsed_seconds;
    
    printf("Processed %zu bytes in %.3f seconds (%.2f MB/s) using %d threads\n", 
           file_size, elapsed_seconds, speed_mbps, num_threads);
    
    // Clean up
    free(threads);
    free(thread_data);
    munmap(output_data, file_size);
    close(output_fd);
    munmap(file_data, file_size);
    close(input_fd);
    
    return 0;
}
