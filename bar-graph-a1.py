import matplotlib.pyplot as plt

# Given results from the test
results = {
    'Server0_VN3': 1087, 'Server2_VN4': 468, 'Server1_VN2': 1035, 'Server1_VN0': 339, 'Server2_VN6': 408,
    'Server0_VN2': 327, 'Server2_VN0': 681, 'Server2_VN7': 254, 'Server0_VN6': 1033, 'Server1_VN6': 141,
    'Server2_VN5': 857, 'Server0_VN1': 1056, 'Server2_VN8': 392, 'Server2_VN3': 891, 'Server2_VN1': 80,
    'Server0_VN0': 167, 'Server1_VN8': 82, 'Server2_VN2': 72, 'Server1_VN1': 103, 'Server1_VN5': 224,
    'Server0_VN7': 88, 'Server1_VN7': 69, 'Server0_VN5': 146
}

# Sorting the results to ensure the bar chart is organized
sorted_results = dict(sorted(results.items()))

# Data for plotting
servers = list(sorted_results.keys())
request_counts = list(sorted_results.values())

plt.figure(figsize=(14, 7))  # Set the figure size for better readability
plt.bar(servers, request_counts, color='blue')
plt.xlabel('Server Instances')
plt.ylabel('Number of Requests Handled')
plt.title('Load Distribution Across Server Instances')
plt.xticks(rotation=90)  # Rotate the x-axis labels for better readability
plt.tight_layout()  # Adjust the layout to fit the labels
plt.show()
