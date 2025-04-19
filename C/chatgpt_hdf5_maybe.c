#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <hdf5.h>

#define SERIAL_PORT "/dev/ttyUSB0"  // Modify this with your Arduino serial port
#define SERVER_PORT 12345           // Network port to listen for Python communication
#define BUFFER_SIZE 256
#define FILENAME "data.h5"

// Global variables for the serial port and network socket
int serial_fd, server_fd, new_sock;
struct sockaddr_in server_addr, client_addr;
socklen_t addr_size;
char buffer[BUFFER_SIZE];

// HDF5 file and dataset
hid_t file_id, dataset_id, dataspace_id;
hsize_t dims[1] = {0};  // Size of the dataset (will grow dynamically)

// Function to initialize serial port
int init_serial_port(const char *port) {
    struct termios options;
    serial_fd = open(port, O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial_fd == -1) {
        perror("Unable to open serial port");
        return -1;
    }
    fcntl(serial_fd, F_SETFL, 0);  // Clear non-blocking flag
    tcgetattr(serial_fd, &options);
    options.c_cflag = B9600 | CS8 | CLOCAL | CREAD;  // 9600 baud, 8 bits, local connection, enable receiver
    options.c_iflag = IGNPAR;  // Ignore parity errors
    options.c_oflag = 0;       // Raw output
    options.c_lflag = 0;       // Raw input
    tcsetattr(serial_fd, TCSANOW, &options);
    return serial_fd;
}

// Function to initialize network socket
int init_network_socket() {
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("Unable to open socket");
        return -1;
    }
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(SERVER_PORT);

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        return -1;
    }
    if (listen(server_fd, 3) < 0) {
        perror("Listen failed");
        return -1;
    }
    addr_size = sizeof(client_addr);
    new_sock = accept(server_fd, (struct sockaddr *)&client_addr, &addr_size);
    if (new_sock < 0) {
        perror("Accept failed");
        return -1;
    }
    return new_sock;
}

// Function to initialize HDF5 file and dataset
void init_hdf5() {
    file_id = H5Fcreate(FILENAME, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (file_id < 0) {
        perror("Unable to create HDF5 file");
        exit(1);
    }

    // Create a dataspace (1D with size 0 to start)
    dataspace_id = H5Screate_simple(1, dims, NULL);

    // Create a dataset
    dataset_id = H5Dcreate(file_id, "/data", H5T_NATIVE_INT, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
}

// Function to write data to HDF5 file
void write_to_hdf5(int value) {
    dims[0]++;  // Increment dataset size
    H5Sset_extent_simple(dataspace_id, 1, dims, NULL);  // Update the dataset's size
    H5Dwrite(dataset_id, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &value);
}

// Function to parse the ASCII string into individual variables
void parse_and_store(const char *data) {
    int var1, var2, var3;  // Assume three integers in the data
    int num_parsed = sscanf(data, "%d,%d,%d", &var1, &var2, &var3);  // Parsing comma-separated values

    if (num_parsed == 3) {
        // Write each parsed variable to HDF5
        write_to_hdf5(var1);
        write_to_hdf5(var2);
        write_to_hdf5(var3);
        printf("Parsed and stored: %d, %d, %d\n", var1, var2, var3);
    } else {
        printf("Failed to parse data: %s\n", data);
    }
}

// Function to handle communication with Arduino and Python program
void *serial_read_thread(void *arg) {
    while (1) {
        int n = read(serial_fd, buffer, sizeof(buffer) - 1);
        if (n > 0) {
            buffer[n] = '\0';  // Null-terminate the string
            parse_and_store(buffer);  // Parse the data and store it in HDF5
        }
    }
    return NULL;
}

void *network_read_thread(void *arg) {
    while (1) {
        int n = read(new_sock, buffer, sizeof(buffer) - 1);
        if (n > 0) {
            buffer[n] = '\0';  // Null-terminate the string
            write(serial_fd, buffer, n);  // Relay data to serial port
        }
    }
    return NULL;
}

int main() {
    // Initialize serial port, network socket, and HDF5 file
    if (init_serial_port(SERIAL_PORT) == -1) {
        exit(1);
    }
    int client_sock = init_network_socket();
    if (client_sock == -1) {
        exit(1);
    }
    init_hdf5();  // Initialize HDF5 file and dataset

    // Create threads for serial and network communication
    pthread_t serial_thread, network_thread;
    pthread_create(&serial_thread, NULL, serial_read_thread, NULL);
    pthread_create(&network_thread, NULL, network_read_thread, NULL);

    // Wait for threads to finish (in reality, this program runs indefinitely)
    pthread_join(serial_thread, NULL);
    pthread_join(network_thread, NULL);

    // Clean up
    H5Dclose(dataset_id);
    H5Sclose(dataspace_id);
    H5Fclose(file_id);
    close(serial_fd);
    close(client_sock);
    return 0;
}
