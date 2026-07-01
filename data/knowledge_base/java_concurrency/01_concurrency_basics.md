# Java 并发编程

## 1. 线程基础

### 线程生命周期
```
NEW → RUNNABLE → (BLOCKED/WAITING/TIMED_WAITING) → TERMINATED
```
- `start()` 启动线程，进入 RUNNABLE
- `synchronized` 竞争失败 → BLOCKED
- `wait()` / `join()` 无参 → WAITING
- `sleep()` / `wait(timeout)` → TIMED_WAITING

### 创建线程的方式
```java
// 1. 继承 Thread
class MyThread extends Thread { public void run() { ... } }

// 2. 实现 Runnable（推荐，避免单继承限制）
class MyTask implements Runnable { public void run() { ... } }
new Thread(new MyTask()).start();

// 3. 实现 Callable + FutureTask（有返回值+异常）
FutureTask<String> task = new FutureTask<>(new Callable<String>() {
    public String call() { return "result"; }
});

// 4. 线程池（实际开发唯一推荐方式）
ExecutorService pool = Executors.newFixedThreadPool(10);
pool.execute(() -> { ... });
```

### 常见面试题
1. **start() 和 run() 的区别？** start() 创建新线程并调用 run()，直接调 run() 是普通方法调用
2. **Callable 和 Runnable 的区别？** Callable 有返回值、抛异常，配合 Future 使用

## 2. 锁机制

### synchronized
```java
// 对象锁
synchronized (obj) { ... }
public synchronized void method() { ... }  // this 锁

// 类锁
public static synchronized void method() { ... }  // Class 对象锁
```
- JDK6+ 锁升级：偏向锁 → 轻量级锁 → 重量级锁
- 可重入：同一线程可重复获取持有的锁

### Lock 接口（JUC）
```java
Lock lock = new ReentrantLock();
lock.lock();
try { ... }
finally { lock.unlock(); }  // 必须在 finally 中释放
```
- `tryLock()` 非阻塞获取，可设置超时
- `Condition`：`await()`/`signal()` 更灵活的等待通知

### synchronized vs Lock
| 维度 | synchronized | Lock |
|------|-------------|------|
| 获取锁 | 阻塞等待 | 可非阻塞/超时/中断 |
| 公平性 | 非公平 | 可选公平 |
| 条件变量 | wait/notify | 多 Condition |
| 自动释放 | ✅ | ❌ 手动 finally |

### 常见面试题
1. **死锁的四个条件？** 互斥、持有等待、不可剥夺、循环等待
2. **如何排查死锁？** jstack 查看线程状态、`ThreadMXBean.findDeadlockedThreads()`

## 3. 线程池

### ThreadPoolExecutor 核心参数
```java
new ThreadPoolExecutor(
    corePoolSize,     // 核心线程数
    maximumPoolSize,  // 最大线程数
    keepAliveTime,    // 空闲线程存活时间
    unit,             // 时间单位
    workQueue,        // 阻塞队列（任务等待）
    handler           // 拒绝策略
);
```

### 提交优先级 vs 执行优先级
- 提交：corePool → workQueue → maximumPool → handler
- 执行：corePool → maximumPool → workQueue

### 拒绝策略
| 策略 | 行为 |
|------|------|
| AbortPolicy（默认） | 抛 RejectedExecutionException |
| CallerRunsPolicy | 由提交线程自己执行 |
| DiscardPolicy | 静默丢弃 |
| DiscardOldestPolicy | 丢弃队列最老的任务 |

### 常见面试题
1. **核心线程数怎么设置？** CPU 密集型 N+1，IO 密集型 2N（N=核心数）
2. **为什么不推荐 Executors 创建线程池？** Fixed/Cached 的队列无界或线程无界，可能 OOM
3. **如何监控线程池？** 重写 beforeExecute/afterExecute，记录队列大小、活跃线程数
