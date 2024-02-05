import matplotlib.pyplot as plt

#With Given Hash Function
data1 = {'Server0': 9352, 'Server2': 469, 'Server1': 157}
data2 = {'Server0': 8320, 'Server2': 469, 'Server1': 157, 'Server3': 1011}
data3 = {'Server0': 8105, 'Server2': 311, 'Server1': 157, 'Server4': 471, 'Server3': 936}
data4 = {'Server0': 7847, 'Server2': 311, 'Server1': 157, 'Server4': 470, 'Server3': 857, 'Server5': 310}

#With Python inbuilt hash function

# data1 ={'Server2': 4294, 'Server0': 1716, 'Server1': 3973}
# data2 ={'Server2': 3981, 'Server1': 2963, 'Server0': 1093, 'Server3': 1946}
# data3 ={'Server4': 4059, 'Server2': 1482, 'Server1': 1714, 'Server3': 1946, 'Server0': 778}
# data4 ={'Server4': 3508, 'Server5': 1013, 'Server2': 1403, 'Server0': 780, 'Server3': 1867, 'Server1': 1401}

# Plotting subplots
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('Bar Graphs of Server Data')

# Subplot 1
axs[0, 0].bar(data1.keys(), data1.values())
axs[0, 0].set_title('n=3 Servers')

# Subplot 2
axs[0, 1].bar(data2.keys(), data2.values())
axs[0, 1].set_title('n=4 Servers')

# Subplot 3
axs[1, 0].bar(data3.keys(), data3.values())
axs[1, 0].set_title('n=5 Servers')

# Subplot 4
axs[1, 1].bar(data4.keys(), data4.values())
axs[1, 1].set_title('n=6 Servers')

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('Load Across Servers with Given Hash.png')
plt.show()
