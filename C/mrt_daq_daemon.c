/* 

This program just acquires data from the Arduino for the MRT (current
using the MRT_Mk3.ino code) and writes it directly to an hdf5 file.
It turns out the serial connection used here is non-blocking, so
commands to the Arduino can be sent while the data are acquired.  One
idea was that this program would look for commands on a port and relay
them, but that seems an unnecessary complication.

The reason for the C program is that I was not able to write python
code that could be guaranteed to keep up with the 250 Hz ASCII stream
from the Arduino.  Thus passing the data along directly is too much,
and we need to save it anyway ... might as well just have the python
work directly with data on disk ... 

 */

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
 
 #define SERIAL_PORT "/dev/ttyACM0"  // Modify this with your Arduino serial port
 #define SERVER_PORT 12345           // Network port to listen for Python communication
 #define BUFFER_SIZE 256
 
 // Global variables for the serial port and network socket
 int serial_fd, server_fd, new_sock;
 struct sockaddr_in server_addr, client_addr;
 socklen_t addr_size;
 char buffer[BUFFER_SIZE];
 
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
   options.c_cflag = B115200 | CS8 | CLOCAL | CREAD;  // baud, 8 bits, local connection, enable receiver
   options.c_iflag = IGNPAR;  // Ignore parity errors
   options.c_oflag = 0;       // Raw output
   options.c_lflag = 0;       // Raw input
   tcsetattr(serial_fd, TCSANOW, &options);
   
   printf("Initialized serial port.\n");
     
   return serial_fd;
 }
 
 // Function to initialize network socket
 int init_network_socket() {
 
   // Huh?
   printf("%i %i \n", AF_INET, SOCK_STREAM);
   
   server_fd = socket(AF_INET, SOCK_STREAM, 0);
   printf("server_fd %i \n", server_fd);
   if (server_fd < 0) {
     perror("Unable to open socket");
     return -1;
   }
 
   printf("Getting some info.\n");
   memset(&server_addr, 0, sizeof(server_addr));
   server_addr.sin_family = AF_INET;
   server_addr.sin_addr.s_addr = INADDR_ANY;
   server_addr.sin_port = htons(SERVER_PORT);
   
   printf("Binding to the server.\n");
   if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
     perror("Bind failed");
     return -1;
   }
 
   printf("Listening to the server.\n");
   if (listen(server_fd, 3) < 0) {
     perror("Listen failed");
     return -1;
   }
 
   printf("Accepting new socket.\n");
   addr_size = sizeof(client_addr);
   printf("Skipping haning command.\n");
   /*
   new_sock = accept(server_fd, (struct sockaddr *)&client_addr, &addr_size);
   
   printf("new_sock %i \n", new_sock);
   if (new_sock < 0) {
     perror("Accept failed");
     return -1;
   }
   */
 
   new_sock = 0;
   
   return new_sock;
 }
 
 // Function to handle communication with Python program and Arduino
 void *serial_read_thread(void *arg) {
   
   printf("Starting serial thread\n");
   while (1) {
     int n = read(serial_fd, buffer, sizeof(buffer) - 1);
     if (n > 0) {
       buffer[n] = '\0';  // Null-terminate the string
       //write_to_file(buffer);  // Write data to text file
       //printf("Received from serial: %s\n", buffer);
       printf("%s", buffer);
     }
   }
   
   return NULL;
 }
 
 int main() {
 
   printf("Hello world!\n");
 
   printf("Initializing serial port.\n");
 
   serial_fd = init_serial_port(SERIAL_PORT);
   if (serial_fd == -1) {
     printf("Unable to open serial port.\n");
     exit(1);
   }
   printf("Opened serial_fd %i \n", serial_fd);
 
   // Punting on the network socket for now.  Code doesn't run ...
   
   printf("Initializing network socket.\n");
 
   int client_sock = init_network_socket();
 
   if (client_sock == -1) {
     printf("Could not initialize network socket.");
     exit(1);
   }
   
 
   // Create threads for serial and network communication
   pthread_t serial_thread;//, network_thread;
   pthread_create(&serial_thread, NULL, serial_read_thread, NULL);
   //pthread_create(&network_thread, NULL, network_read_thread, NULL);
 
   // Wait for threads to finish (in reality, this program runs indefinitely)
   pthread_join(serial_thread, NULL);
   //pthread_join(network_thread, NULL);
 
   close(serial_fd);
   
   return 0;
   
 }
 