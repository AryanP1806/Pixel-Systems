import 'package:flutter/material.dart';
import '../screens/home_screen.dart';
import '../screens/product_list_screen.dart';
import '../screens/customer_list_screen.dart';
import '../screens/rental_list_screen.dart';
import '../screens/approval_dashboard_screen.dart';
import '../screens/login_screen.dart';
import '../services/api_service.dart';

class AppDrawer extends StatelessWidget {
  final ApiService apiService;
  const AppDrawer({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary,
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Icon(Icons.computer, color: Colors.white, size: 40),
                SizedBox(height: 10),
                Text(
                  "Pixel Systems",
                  style: TextStyle(color: Colors.white, fontSize: 24),
                ),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.dashboard),
            title: const Text('Dashboard'),
            onTap: () => Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (_) => HomeScreen(apiService: apiService),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.inventory),
            title: const Text('Assets'),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ProductListScreen(apiService: apiService),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.people),
            title: const Text('Customers'),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => CustomerListScreen(apiService: apiService),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.shopping_bag),
            title: const Text('Rentals'),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => RentalListScreen(apiService: apiService),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.verified_user),
            title: const Text('Approvals'),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ApprovalDashboardScreen(apiService: apiService),
              ),
            ),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Logout'),
            onTap: () => Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            ),
          ),
        ],
      ),
    );
  }
}
