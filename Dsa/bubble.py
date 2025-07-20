l = [6,42,5,1,53,8,3]


def insertion_sort(n):
    for i in range(n):
        for j in range(n-1):
            if l[i] < l[j]:
                temp = l[i]
                l[i] = l[j]
                l[j] = temp
    print(f"List has {l}")
    print("Highest Ones:")
    for i in range(n-1,n-6,-1):
        print(l[i], end=", ")
    print()


def adding():
    while True:
        try:
            a = int(input("Enter data(leave blank if none): "))
            l.append(a)
        
        except :
            return


def selection_sort(n):
    pass

def bubble_sort(n):
    for i in range(n):
        for j in range(n-1):
            if l[i] < l[j]:
                temp = l[i]
                l[i] = l[j]
                l[j] = temp
    print(f"List has {l}")
    print("Highest Ones:")
    for i in range(n-1,n-6,-1):
        print(l[i], end=", ")
    print()


run = True
while run:
    
    a = int(input("Enter your choice\n1.insertion Sort\n2.Selection Sort\n3.Enter data\n4.Bubble Sort>"))
    match(a):
        case 1:
            insertion_sort(len(l))
            

        case 2:
            pass

        case 3:
            adding()
        
        case 4:
            bubble_sort(len(l))
        case default:
            print("Enter valid no.")