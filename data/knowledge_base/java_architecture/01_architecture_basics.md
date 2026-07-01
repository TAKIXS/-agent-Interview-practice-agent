# Java 架构设计

## 1. 设计模式

### 单例模式 (Singleton)
```java
// 双重检查锁定（DCL）— 最常用
public class Singleton {
    private static volatile Singleton instance;
    private Singleton() {}
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```
- `volatile` 防止指令重排（new 对象不是原子操作）
- 枚举单例是 Effective Java 推荐方式（防反射攻击、防序列化破坏）

### 工厂模式 (Factory)
- 简单工厂：一个工厂类，根据参数创建不同产品
- 工厂方法：每个产品有对应的工厂，符合开闭原则
- 抽象工厂：创建产品族

### 策略模式 (Strategy)
```java
// 定义策略接口
interface PaymentStrategy { void pay(int amount); }
// 具体策略
class AliPay implements PaymentStrategy { ... }
class WechatPay implements PaymentStrategy { ... }
// 上下文
class PaymentContext {
    private PaymentStrategy strategy;
    public void pay(int amount) { strategy.pay(amount); }
}
```
- 替代大量 if-else，符合开闭原则
- Spring 中使用 `@Autowired Map<String, Strategy>` 自动注入所有实现

### 常见面试题
1. **你实际项目中用过哪些设计模式？** 单例（Bean）、工厂（BeanFactory）、策略（支付）、模板方法（JdbcTemplate）、代理（AOP）、观察者（事件监听）
2. **动态代理的应用场景？** AOP、RPC 远程调用、缓存代理、延迟加载

## 2. 微服务架构

### 核心组件
| 组件 | 方案 |
|------|------|
| 服务注册发现 | Nacos / Eureka / Consul |
| 配置中心 | Nacos / Apollo / Spring Cloud Config |
| 网关 | Spring Cloud Gateway / Zuul |
| 远程调用 | Feign / Dubbo / gRPC |
| 负载均衡 | Ribbon / LoadBalancer |
| 熔断降级 | Sentinel / Resilience4j |
| 链路追踪 | SkyWalking / Zipkin |

### CAP 理论
- **C**onsistency（一致性）：所有节点同一时刻数据相同
- **A**vailability（可用性）：每个请求都能获得响应
- **P**artition tolerance（分区容错）：网络分区时系统仍能工作
- CAP 只能同时满足两个，分布式系统必须选 P

### 常见面试题
1. **分布式事务解决方案？** 2PC、TCC、Seata AT 模式、本地消息表、RocketMQ 事务消息
2. **服务雪崩如何防止？** 熔断（断路器）、限流（令牌桶/漏桶）、降级（兜底逻辑）

## 3. 分布式系统

### Redis
- 缓存穿透：布隆过滤器 / 缓存空值
- 缓存击穿：互斥锁 / 永不过期 + 异步刷新
- 缓存雪崩：随机过期时间 / 多级缓存 / 限流降级
- 持久化：RDB（快照）vs AOF（追加日志）
- 集群模式：主从、哨兵、Cluster

### 消息队列
- 解耦：服务间不直接调用
- 削峰：瞬时流量缓冲
- 异步：非核心链路异步化
- 常见选型：RabbitMQ、Kafka、RocketMQ

### 常见面试题
1. **Redis 为什么快？** 纯内存、单线程避免锁竞争、IO 多路复用、RESP 协议简洁
2. **Kafka 如何保证消息不丢失？** 生产者 acks=all、broker 多副本 ISR、消费者手动提交 offset
