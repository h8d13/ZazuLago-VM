#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#define BUFFER_SIZE (16 * 1024 * 1024) // 16MB per thread
#define MAX_THREADS 32

typedef struct {
    uint8_t *buffer;
    size_t length;
    uint64_t magic_number;
    size_t thread_id;
} ThreadData;

// Process data in 64-bit chunks
void process_data(uint8_t *buffer, size_t length, uint64_t magic_number) {
    uint64_t *buffer64 = (uint64_t *)buffer;
    size_t length64 = length / 8;
    
    for (size_t i = 0; i < length64; i++) {
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
    uint8_t *remainder = buffer + (length64 * 8);
    size_t remaining_bytes = length % 8;
    
    for (size_t i = 0; i < remaining_bytes; i++) {
        remainder[i] ^= (uint8_t)(magic_number >> (8 * (i % 8)));
    }
}

void* thread_process_data(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    
    // Generate a unique seed for this thread based on thread_id
    uint64_t thread_magic = data->magic_number ^ (data->thread_id * 0x123456789ABCDEFULL);
    
    process_data(data->buffer, data->length, thread_magic);
    
    return NULL;
}

// Function to get number of available CPU cores
int get_num_cores() {
    int num_cores = 1; // Default to 1 if detection fails
    
    #ifdef _SC_NPROCESSORS_ONLN
    num_cores = sysconf(_SC_NPROCESSORS_ONLN);
    if (num_cores < 1) num_cores = 1;
    #endif
    
    return num_cores;
}

int main(int argc, char *argv[]) {
    if (argc < 4 || argc > 5) {
        fprintf(stderr, "Usage: %s <input_file> <output_file> <magic_number> [num_threads]\n", argv[0]);
        return 1;
    }
    
    const char *input_filename = argv[1];
    const char *output_filename = argv[2];
    uint64_t magic_number = strtoull(argv[3], NULL, 0);
    
    // Determine number of threads (default to available cores)
    int num_threads = get_num_cores();
    if (argc == 5) {
        int requested_threads = atoi(argv[4]);
        if (requested_threads > 0) {
            num_threads = requested_threads;
        }
    }
    if (num_threads > MAX_THREADS) num_threads = MAX_THREADS;
    
    printf("Using %d threads on this system\n", num_threads);
    
    // Get file size
    struct stat st;
    if (stat(input_filename, &st) != 0) {
        perror("Failed to get file size");
        return 1;
    }
    size_t file_size = st.st_size;
    
    // Adjust number of threads for small files
    if (file_size < num_threads * BUFFER_SIZE / 2) {
        num_threads = (file_size / BUFFER_SIZE) + 1;
        if (num_threads < 1) num_threads = 1;
        printf("Adjusted to %d threads based on file size\n", num_threads);
    }
    
    FILE *input_file = fopen(input_filename, "rb");
    if (!input_file) {
        perror("Failed to open input file");
        return 1;
    }
    
    FILE *output_file = fopen(output_filename, "wb");
    if (!output_file) {
        perror("Failed to open output file");
        fclose(input_file);
        return 1;
    }
    
    // Start timing
    clock_t start = clock();
    
    // Allocate memory for thread data
    ThreadData *thread_data = malloc(num_threads * sizeof(ThreadData));
    pthread_t *threads = malloc(num_threads * sizeof(pthread_t));
    uint8_t **buffers = malloc(num_threads * sizeof(uint8_t*));
    
    if (!thread_data || !threads || !buffers) {
        perror("Failed to allocate memory for thread data");
        free(buffers);
        free(threads);
        free(thread_data);
        fclose(input_file);
        fclose(output_file);
        return 1;
    }
    
    // Allocate buffer for each thread
    for (int i = 0; i < num_threads; i++) {
        buffers[i] = malloc(BUFFER_SIZE);
        if (!buffers[i]) {
            perror("Failed to allocate buffer");
            // Clean up already allocated buffers
            for (int j = 0; j < i; j++) {
                free(buffers[j]);
            }
            free(buffers);
            free(threads);
            free(thread_data);
            fclose(input_file);
            fclose(output_file);
            return 1;
        }
    }
    
    // Process file in chunks
    size_t total_processed = 0;
    
    while (total_processed < file_size) {
        int active_threads = 0;
        
        // Read chunks and assign to threads
        for (int i = 0; i < num_threads && total_processed < file_size; i++) {
            size_t bytes_to_read = BUFFER_SIZE;
            if (total_processed + bytes_to_read > file_size) {
                bytes_to_read = file_size - total_processed;
            }
            
            // Read chunk from file
            size_t bytes_read = fread(buffers[i], 1, bytes_to_read, input_file);
            if (bytes_read < bytes_to_read && !feof(input_file)) {
                perror("Error reading from file");
                for (int j = 0; j < num_threads; j++) {
                    free(buffers[j]);
                }
                free(buffers);
                free(threads);
                free(thread_data);
                fclose(input_file);
                fclose(output_file);
                return 1;
            }
            
            thread_data[i].buffer = buffers[i];
            thread_data[i].length = bytes_read;
            thread_data[i].magic_number = magic_number;
            thread_data[i].thread_id = i;
            
            int ret = pthread_create(&threads[i], NULL, thread_process_data, &thread_data[i]);
            if (ret != 0) {
                fprintf(stderr, "Failed to create thread %d\n", i);
                for (int j = 0; j < num_threads; j++) {
                    free(buffers[j]);
                }
                free(buffers);
                free(threads);
                free(thread_data);
                fclose(input_file);
                fclose(output_file);
                return 1;
            }
            
            active_threads++;
            total_processed += bytes_read;
        }
        
        // Wait for all active threads to complete
        for (int i = 0; i < active_threads; i++) {
            pthread_join(threads[i], NULL);
            
            // Write processed data to output file
            if (fwrite(thread_data[i].buffer, 1, thread_data[i].length, output_file) != thread_data[i].length) {
                perror("Failed to write to output file");
                for (int j = 0; j < num_threads; j++) {
                    free(buffers[j]);
                }
                free(buffers);
                free(threads);
                free(thread_data);
                fclose(input_file);
                fclose(output_file);
                return 1;
            }
        }
    }
    
    // Calculate and display performance metrics
    clock_t end = clock();
    double elapsed_time = (double)(end - start) / CLOCKS_PER_SEC;
    double speed_mbps = (file_size / (1024.0 * 1024.0)) / elapsed_time;
    
    printf("Processed %zu bytes in %.2f seconds (%.2f MB/s) using %d threads\n", 
           file_size, elapsed_time, speed_mbps, num_threads);
    
    // Clean up
    for (int i = 0; i < num_threads; i++) {
        free(buffers[i]);
    }
    free(buffers);
    free(thread_data);
    free(threads);
    fclose(input_file);
    fclose(output_file);
    
    return 0;
}
