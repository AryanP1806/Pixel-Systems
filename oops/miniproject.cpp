#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <ctime>
#include <limits>

using namespace std;

// 🌈 Console Decorations
void printLine(char ch = '=', int len = 60) {
    for (int i = 0; i < len; i++) cout << ch;
    cout << endl;
}

void title(string text) {
    printLine('=');
    cout << setw(35 + text.size()/2) << text << endl;
    printLine('=');
}

// 🧾 Purchase Record Structure
struct Purchase {
    string productName;
    int quantity;
    double totalCost;
    string date;
};

// 📦 Product Class
class Product {
public:
    int id;
    string name;
    double price;
    double cost;
    int stock;
    int sold;

    Product(int i, string n, double c, double p, int s)
        : id(i), name(n), cost(c), price(p), stock(s), sold(0) {}

    double profit() const {
        return (price - cost) * sold;
    }
};

// 📊 Inventory Management System
class InventorySystem {
    vector<Product> products;
    vector<Purchase> purchases;

public:
    // 🟢 Add sample products
    InventorySystem() {
        products.push_back(Product(1, "Laptop", 45000, 60000, 10));
        products.push_back(Product(2, "Monitor", 7000, 9500, 20));
        products.push_back(Product(3, "Keyboard", 600, 900, 50));
        products.push_back(Product(4, "Mouse", 300, 550, 60));
        products.push_back(Product(5, "Printer", 5000, 7000, 15));
    }

    // 🧾 List all products
    void listProducts() {
        title("PRODUCT LIST");
        cout << left << setw(5) << "ID" 
             << setw(20) << "Name" 
             << setw(10) << "Cost" 
             << setw(10) << "Price" 
             << setw(10) << "Stock" << endl;
        printLine('-');
        for (auto &p : products) {
            cout << left << setw(5) << p.id
                 << setw(20) << p.name
                 << setw(10) << p.cost
                 << setw(10) << p.price
                 << setw(10) << p.stock << endl;
        }
        printLine('=');
    }

    // 🔍 Display individual product
    void displayProduct() {
        int id;
        cout << "Enter Product ID: ";
        cin >> id;
        for (auto &p : products) {
            if (p.id == id) {
                title("PRODUCT DETAILS");
                cout << "Product ID   : " << p.id << endl;
                cout << "Name         : " << p.name << endl;
                cout << "Cost Price   : " << p.cost << endl;
                cout << "Sell Price   : " << p.price << endl;
                cout << "Stock Left   : " << p.stock << endl;
                cout << "Units Sold   : " << p.sold << endl;
                printLine('=');
                return;
            }
        }
        cout << "❌ Product not found!\n";
    }

    // 🛒 Purchase (Add Stock)
    void purchaseProduct() {
        int id, qty;
        cout << "Enter Product ID: ";
        cin >> id;
        cout << "Enter Quantity Purchased: ";
        cin >> qty;

        for (auto &p : products) {
            if (p.id == id) {
                p.stock += qty;
                double total = p.cost * qty;

                // Record date
                time_t now = time(0);
                string dt = ctime(&now);
                dt.pop_back(); // remove newline

                purchases.push_back({p.name, qty, total, dt});

                cout << "✅ Purchased " << qty << " units of " << p.name << " successfully!\n";
                cout << "Total Cost: ₹" << total << endl;
                return;
            }
        }
        cout << "❌ Product not found!\n";
    }

    // 🚚 Shipping (Reduce Stock)
    void shipProduct() {
        int id, qty;
        cout << "Enter Product ID to Ship: ";
        cin >> id;
        cout << "Enter Quantity: ";
        cin >> qty;

        for (auto &p : products) {
            if (p.id == id) {
                if (qty > p.stock) {
                    cout << "⚠️ Not enough stock!\n";
                    return;
                }
                p.stock -= qty;
                p.sold += qty;
                cout << "🚚 Shipped " << qty << " units of " << p.name << endl;
                return;
            }
        }
        cout << "❌ Product not found!\n";
    }

    // 📦 Balance Stock
    void balanceStock() {
        title("BALANCE STOCK");
        for (auto &p : products) {
            cout << setw(20) << p.name << " : " << p.stock << " units left\n";
        }
        printLine('=');
    }

    // 💰 Profit / Loss Calculation
    void calculateProfitLoss() {
        double totalProfit = 0, totalInvestment = 0;
        for (auto &p : products) {
            totalProfit += p.profit();
            totalInvestment += p.cost * (p.stock + p.sold);
        }
        title("PROFIT / LOSS REPORT");
        cout << "Total Investment: ₹" << totalInvestment << endl;
        cout << "Total Profit    : ₹" << totalProfit << endl;
        if (totalProfit > 0)
            cout << "📈 Status: PROFIT" << endl;
        else
            cout << "📉 Status: LOSS" << endl;
        printLine('=');
    }

    // 🗓️ Purchase Report (From-To)
    void purchaseReport() {
        title("PURCHASE REPORT");
        cout << left << setw(20) << "Product"
             << setw(10) << "Qty"
             << setw(15) << "Total Cost"
             << setw(25) << "Date" << endl;
        printLine('-');
        for (auto &r : purchases) {
            cout << left << setw(20) << r.productName
                 << setw(10) << r.quantity
                 << setw(15) << r.totalCost
                 << setw(25) << r.date << endl;
        }
        printLine('=');
    }

    // 🧭 Main Menu
    void menu() {
        int choice;
        do {
            title("INVENTORY MANAGEMENT SYSTEM");
            cout << "1. List All Products\n";
            cout << "2. Display Product Info\n";
            cout << "3. Purchase Product\n";
            cout << "4. Ship Product\n";
            cout << "5. Balance Stock\n";
            cout << "6. Profit/Loss Report\n";
            cout << "7. Purchase Report\n";
            cout << "0. Exit\n";
            printLine('-');
            cout << "Enter your choice: ";
            cin >> choice;
            cout << endl;

            switch (choice) {
                case 1: listProducts(); break;
                case 2: displayProduct(); break;
                case 3: purchaseProduct(); break;
                case 4: shipProduct(); break;
                case 5: balanceStock(); break;
                case 6: calculateProfitLoss(); break;
                case 7: purchaseReport(); break;
                case 0: cout << "👋 Exiting... Thank you!\n"; break;
                default: cout << "❌ Invalid Choice!\n";
            }
            cout << endl;
        } while (choice != 0);
    }
};

// 🚀 MAIN FUNCTION
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    InventorySystem inv;
    inv.menu();
    return 0;
}
