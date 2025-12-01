import 'package:flutter/material.dart';
import '../models/rental.dart';
import '../services/api_service.dart';

class RentalListScreen extends StatelessWidget {
  final ApiService apiService;

  const RentalListScreen({super.key, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Active Rentals")),
      body: FutureBuilder<List<Rental>>(
        future: apiService.getRentals(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text("No rentals found."));
          }

          final rentals = snapshot.data!;

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: rentals.length,
            itemBuilder: (context, index) {
              final rental = rentals[index];
              final isOngoing = rental.status.toLowerCase() == 'ongoing';

              return Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  leading: CircleAvatar(
                    backgroundColor: isOngoing
                        ? Colors.green.shade50
                        : Colors.grey.shade100,
                    child: Icon(
                      Icons.shopping_bag_outlined,
                      color: isOngoing ? Colors.green : Colors.grey,
                    ),
                  ),
                  title: Text(
                    rental.customerName,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text("Asset: ${rental.assetId}"),
                      Text(
                        "Start Date: ${rental.startDate}",
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                    ],
                  ),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: isOngoing
                          ? Colors.green.withOpacity(0.1)
                          : Colors.grey.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isOngoing
                            ? Colors.green.withOpacity(0.5)
                            : Colors.grey.withOpacity(0.5),
                      ),
                    ),
                    child: Text(
                      rental.status.toUpperCase(),
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: isOngoing ? Colors.green[700] : Colors.grey[700],
                      ),
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
