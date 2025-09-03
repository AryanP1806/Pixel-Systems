#include <stdio.h>
#include <graphics.h>

int main() {
    int gd = DETECT, gm;
    initgraph(&gd, &gm, "");

    // Draw a simple rectangle
    rectangle(100, 100, 200, 200);
    floodfill(150, 150, WHITE);

    // Draw a circle
    circle(300, 150, 50);
    floodfill(300, 150, WHITE);

    // Draw a line
    line(400, 100, 500, 200);

    getch();
    closegraph();
    return 0;
}