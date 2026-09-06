# scheduling

`DailyMonitor` owns one coalesced APScheduler interval job with a single concurrent
instance. Its callback is the application monitor; library-specific details stay here.
