#include <stdio.h>
#include <stdlib.h>

struct Node
{
    int node;
    struct Node *next;
}*first=NULL;


void create(int a[],int n){
    int i;
    struct Node *t, *last;
    first = (struct Node *)malloc(sizeof(struct Node));
    first->node = a[0];
    first->next = NULL;
    last = first;

    for(i = 1; i < n; i++){
        t = (struct Node *)malloc(sizeof(struct Node));
        t->node = a[i];
        t->next = NULL;
        last->next = t;
        last = t;
    }
}

void display(struct Node *p){
    while(p){
        printf("%d ", p->node);
        p = p->next;
    }
}
int main(){
    int a[] = {1,4,6,8,3,2,5};

    create(a,6);
    display(first);
    return 0;
}