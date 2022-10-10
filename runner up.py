n = int(input())
arr = list(map(int, input().split()))
for i in range(arr.count(max(arr))):
  arr.remove(max(arr))
print(max(arr))
