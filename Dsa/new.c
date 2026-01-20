#include <stdio.h>
int num = 5;
struct employee
{
    char name[20];
    float salary;
};

int main()
{
    struct employee e[num]; 
    for (int i = 0; i < num; i++){
        printf("\nEnter Employee Name: ");
        scanf("%s", e[i].name); 
        printf("\nEnter Employee Salary: ");
        scanf("%f", &e[i].salary);
    }
    int highest_sal= e[0].salary;
    char emp_name = e[0].name;
    for(int i = 0; i<num-1;i++){
        if(e[i].salary < e[i+1].salary ){
            highest_sal = e[i+1].salary;
            emp_name = e[i+1].name;
        }
    }
    printf("%s has highest salary of %d",emp_name,highest_sal);
    return 0;
}
