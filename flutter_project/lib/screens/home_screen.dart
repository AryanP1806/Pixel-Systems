import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/app_drawer.dart';
import 'product_list_screen.dart';
import 'customer_list_screen.dart';
import 'rental_list_screen.dart';
import 'approval_dashboard_screen.dart';

class HomeScreen extends StatelessWidget {
  final ApiService apiService;
  const HomeScreen({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Dashboard")),
      drawer: AppDrawer(apiService: apiService),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.count(
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          children: [
            _buildCard(
              context,
              "Assets",
              Icons.laptop,
              Colors.blue,
              () => ProductListScreen(apiService: apiService),
            ),
            _buildCard(
              context,
              "Customers",
              Icons.people,
              Colors.orange,
              () => CustomerListScreen(apiService: apiService),
            ),
            _buildCard(
              context,
              "Rentals",
              Icons.shopping_bag,
              Colors.green,
              () => RentalListScreen(apiService: apiService),
            ),
            _buildCard(
              context,
              "Approvals",
              Icons.approval,
              Colors.purple,
              () => ApprovalDashboardScreen(apiService: apiService),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCard(
    BuildContext context,
    String title,
    IconData icon,
    Color color,
    Widget Function() page,
  ) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () =>
            Navigator.push(context, MaterialPageRoute(builder: (_) => page())),
        borderRadius: BorderRadius.circular(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircleAvatar(
              backgroundColor: color.withOpacity(0.2),
              radius: 30,
              child: Icon(icon, color: color, size: 30),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
