import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'foreground_service_handler.dart';

class ForegroundServiceManager {
  static void init() {
    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'emergency_alert_channel',
        channelName: 'Emergency Alert Service',
        channelDescription: 'Monitors emergency alerts in your area.',
        channelImportance: NotificationChannelImportance.HIGH,
        priority: NotificationPriority.HIGH,
      ),
      iosNotificationOptions: const IOSNotificationOptions(
        showNotification: true,
        playSound: false,
      ),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.repeat(10000),
        autoRunOnBoot: true,
        allowWakeLock: true,
      ),
    );
  }

  static Future<void> startService() async {
    if (await FlutterForegroundTask.isRunningService) {
      return;
    }

    await FlutterForegroundTask.startService(
      serviceId: 1001,
      notificationTitle: '🚨 Emergency Alert Active',
      notificationText: 'Monitoring alerts in your area...',
      callback: startForegroundServiceCallback,
    );
  }

  static Future<void> stopService() async {
    await FlutterForegroundTask.stopService();
  }
}