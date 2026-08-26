import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'alert_service.dart';

@pragma('vm:entry-point')
void startForegroundServiceCallback() {
  FlutterForegroundTask.setTaskHandler(EmergencyTaskHandler());
}

class EmergencyTaskHandler extends TaskHandler {
  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    print('[ForegroundService] Started.');
    AlertService.start(); // Initiates WebSocket connection
  }

  @override
  Future<void> onRepeatEvent(DateTime timestamp) async {
    // Task options require repeat action; keep idle unless ping is needed
  }

  @override
  Future<void> onDestroy(DateTime timestamp) async {
    print('[ForegroundService] Destroyed.');
    AlertService.stop();
  }
}