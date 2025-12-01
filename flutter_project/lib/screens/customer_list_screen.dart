import 'package:flutter/material.dart';
import '../models/customer.dart';
import '../services/api_service.dart';

class CustomerListScreen extends StatelessWidget {
  final ApiService apiService;
  const CustomerListScreen({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Customers")),
      body: FutureBuilder<List<Customer>>(
        future: apiService.getCustomers(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text("No Customers Found"));
          }

          return ListView.builder(
            itemCount: snapshot.data!.length,
            itemBuilder: (ctx, i) {
              final c = snapshot.data![i];
              return ListTile(
                leading: CircleAvatar(child: Text(c.name[0])),
                title: Text(c.name),
                subtitle: Text("${c.phone} | ${c.address}"),
              );
            },
          );
        },
      ),
    );
  }
}
