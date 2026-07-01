# Java 基础核心

## 1. 面向对象三大特性

### 封装 (Encapsulation)
- 隐藏内部实现细节，只暴露必要的接口
- 通过 `private` 字段 + `public` getter/setter 实现
- 优势：提高安全性、可维护性，降低耦合

```java
public class User {
    private String name;
    private int age;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) {
        if (age < 0) throw new IllegalArgumentException("年龄不能为负");
        this.age = age;
    }
}
```

### 继承 (Inheritance)
- 子类继承父类的属性和方法，实现代码复用
- `extends` 关键字，Java 单继承
- 方法重写 `@Override`：子类覆盖父类方法，运行时多态

### 多态 (Polymorphism)
- 编译时多态：方法重载（同一个方法名，不同参数列表）
- 运行时多态：父类引用指向子类对象，调用重写方法时执行子类版本
- 核心机制：动态绑定（virtual method invocation）

### 常见面试题
1. **抽象类和接口的区别？** JDK8+ 接口可以有 default 方法，但抽象类可以有构造器和状态
2. **重写 (Override) 和重载 (Overload) 的区别？** 重写是运行时多态，重载是编译时多态
3. **为什么 Java 不支持多继承？** 避免菱形继承问题（diamond problem）

## 2. Java 集合框架

### List vs Set vs Map
| 类型 | 有序 | 可重复 | 常用实现 |
|------|------|--------|----------|
| List | ✅ | ✅ | ArrayList, LinkedList |
| Set | ❌ | ❌ | HashSet, TreeSet |
| Map | ❌ | Key 唯一 | HashMap, TreeMap |

### HashMap 原理（高频）
- JDK8+：数组 + 链表/红黑树
- put 流程：计算 hash → 定位桶 → 链表插入 → 超过 8 转红黑树
- 扩容：默认容量 16，负载因子 0.75，2 倍扩容
- **线程不安全**：并发 put 可能导致死循环（JDK7）或数据丢失，用 ConcurrentHashMap 替代

### ArrayList vs LinkedList
- ArrayList：动态数组，随机访问 O(1)，插入删除 O(n)
- LinkedList：双向链表，随机访问 O(n)，头尾插入 O(1)

### 常见面试题
1. **HashMap 和 Hashtable 的区别？** Hashtable 线程安全但性能差，不推荐使用
2. **ConcurrentHashMap 如何保证线程安全？** JDK8 用 CAS + synchronized 锁桶首节点
3. **ArrayList 扩容机制？** 1.5 倍扩容（newCapacity = oldCapacity + oldCapacity >> 1）

## 3. 异常处理

### 异常体系
```
Throwable
├── Error（不可恢复，如 OutOfMemoryError）
└── Exception
    ├── RuntimeException（非受检异常，如 NullPointerException）
    └── 受检异常（必须 try-catch 或 throws，如 IOException）
```

### try-with-resources（JDK7+）
```java
try (BufferedReader br = new BufferedReader(new FileReader("file.txt"))) {
    return br.readLine();
} // 自动调用 close()，无需 finally
```

### 常见面试题
1. **finally 一定会执行吗？** 除了 `System.exit(0)` 或 JVM 崩溃
2. **return 在 try 和 finally 中都有时返回哪个？** finally 的 return 会覆盖 try 的

## 4. 字符串

### String / StringBuilder / StringBuffer
| 类 | 可变 | 线程安全 | 场景 |
|----|------|----------|------|
| String | ❌ | — | 少量拼接 |
| StringBuilder | ✅ | ❌ | 单线程频繁拼接 |
| StringBuffer | ✅ | ✅ | 多线程 |

### 字符串常量池
- `String s = "hello"` 放入常量池，复用
- `new String("hello")` 在堆上创建新对象，不放入常量池
- `intern()` 将堆上字符串放入常量池并返回引用

### 常见面试题
1. **`==` 和 `equals()` 的区别？** `==` 比较引用地址，`equals()` 比较内容
2. **为什么 String 设计为不可变？** 安全性、常量池复用、HashMap key 稳定性
