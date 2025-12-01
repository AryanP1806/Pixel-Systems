// import 'package:flutter/material.dart';
// import 'screens/login_screen.dart';

// void main() {
//   runApp(const MyApp());
// }

// class MyApp extends StatelessWidget {
//   const MyApp({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       title: 'Pixel Systems',
//       debugShowCheckedModeBanner: false, // Removes the "Debug" banner
//       // 🎨 THIS IS YOUR DESIGN THEME
//       theme: ThemeData(
//         useMaterial3: true,

//         // 1. Define the Color Palette
//         colorScheme: ColorScheme.fromSeed(
//           seedColor: const Color(0xFF2563EB), // Professional Tech Blue
//           brightness: Brightness.light,
//           background: const Color(
//             0xFFF3F4F6,
//           ), // Light grey background for the app
//         ),

//         // 2. Define Global Text Styles
//         textTheme: const TextTheme(
//           headlineMedium: TextStyle(
//             fontSize: 24,
//             fontWeight: FontWeight.bold,
//             color: Colors.black87,
//           ),
//           bodyLarge: TextStyle(fontSize: 16, color: Colors.black87),
//         ),

//         // 3. Global Button Style (Rounded & Blue)
//         elevatedButtonTheme: ElevatedButtonThemeData(
//           style: ElevatedButton.styleFrom(
//             backgroundColor: const Color(0xFF2563EB), // Button color
//             foregroundColor: Colors.white, // Text color
//             padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
//             elevation: 2,
//             shape: RoundedRectangleBorder(
//               borderRadius: BorderRadius.circular(12),
//             ),
//             textStyle: const TextStyle(
//               fontSize: 16,
//               fontWeight: FontWeight.w600,
//             ),
//           ),
//         ),

//         // 4. Global Input Field Style
//         inputDecorationTheme: InputDecorationTheme(
//           filled: true,
//           fillColor: Colors.white,
//           border: OutlineInputBorder(
//             borderRadius: BorderRadius.circular(12),
//             borderSide: BorderSide.none,
//           ),
//           enabledBorder: OutlineInputBorder(
//             borderRadius: BorderRadius.circular(12),
//             borderSide: BorderSide(color: Colors.grey.shade200),
//           ),
//           focusedBorder: OutlineInputBorder(
//             borderRadius: BorderRadius.circular(12),
//             borderSide: const BorderSide(color: Color(0xFF2563EB), width: 2),
//           ),
//           contentPadding: const EdgeInsets.symmetric(
//             horizontal: 20,
//             vertical: 16,
//           ),
//         ),
//       ),

//       home: const LoginScreen(),
//     );
//   }
// }
import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Pixel Systems',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
      ),
      // Instead of LoginScreen, we load this AutoLoginWrapper
      home: const AutoLoginWrapper(),
    );
  }
}

// This widget does the "Direct Login" magic
class AutoLoginWrapper extends StatefulWidget {
  const AutoLoginWrapper({super.key});

  @override
  State<AutoLoginWrapper> createState() => _AutoLoginWrapperState();
}

class _AutoLoginWrapperState extends State<AutoLoginWrapper> {
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _performAutoLogin();
  }

  void _performAutoLogin() async {
    print("🔄 Attempting Auto-Login...");

    // HARDCODED CREDENTIALS
    // Ensure this user exists in Django (python manage.py createsuperuser)
    bool success = await _apiService.login("mobile", "pass1234");

    if (!mounted) return;

    if (success) {
      print("✅ Auto-Login Success! Going to Dashboard.");
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => HomeScreen(apiService: _apiService)),
      );
    } else {
      print("❌ Auto-Login Failed. Going to Manual Login.");
      // If auto-login fails (wrong IP or server down), go to manual login screen
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 20),
            Text("Logging in automatically...", style: TextStyle(fontSize: 16)),
            SizedBox(height: 10),
            Text(
              "Check your Django Server terminal!",
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
