# Spring 框架面试核心

## 1. Spring IoC（控制反转）

### 核心概念
将对象的创建和管理交给 Spring 容器，开发者只需声明依赖关系。

```java
// 传统方式：自己 new（强耦合）
UserService service = new UserServiceImpl();

// IoC：容器注入（松耦合）
@Autowired
private UserService service;
```

### Bean 生命周期
```
实例化 → 属性注入 → BeanNameAware → BeanFactoryAware
→ BeanPostProcessor(before) → @PostConstruct
→ InitializingBean.afterPropertiesSet → 自定义init-method
→ BeanPostProcessor(after) → 就绪
→ @PreDestroy → DisposableBean.destroy → 自定义destroy-method
```

### Bean 作用域
| 作用域 | 说明 |
|--------|------|
| singleton（默认） | 整个容器只有一个实例 |
| prototype | 每次获取都创建新实例 |
| request | 每个 HTTP 请求一个 |
| session | 每个 HTTP 会话一个 |

### 常见面试题
1. **BeanFactory 和 ApplicationContext 的区别？** BeanFactory 懒加载，ApplicationContext 扩展了事件/国际化/AOP
2. **@Autowired 和 @Resource 区别？** @Autowired 按类型，@Resource 按名称（JSR-250）
3. **循环依赖如何解决？** Spring 三级缓存：singletonObjects → earlySingletonObjects → singletonFactories

## 2. Spring AOP（面向切面编程）

### 核心概念
- **切面 (Aspect)**：横切关注点的模块化（如日志、事务）
- **通知 (Advice)**：`@Before` / `@After` / `@Around` / `@AfterReturning` / `@AfterThrowing`
- **切入点 (Pointcut)**：execution 表达式，匹配哪些方法
- **织入 (Weaving)**：编译期/类加载期/运行期（Spring 用运行期代理）

### JDK 动态代理 vs CGLIB
| 维度 | JDK 动态代理 | CGLIB |
|------|-------------|-------|
| 原理 | 基于接口 | 基于继承（子类） |
| 要求 | 必须有接口 | 不能是 final 类/方法 |
| 性能 | 反射较慢 | ASM 字节码，更快 |
| Spring 默认 | 有接口时用 | 无接口时用 |

### 常见面试题
1. **AOP 的应用场景？** 日志、事务、权限校验、性能监控、缓存
2. **@Transactional 失效场景？** 同类方法调用（this.method() 不走代理）、非 public 方法、异常被 catch

## 3. Spring Boot

### 自动配置原理
```
@SpringBootApplication
  └── @EnableAutoConfiguration
       └── @Import(AutoConfigurationImportSelector.class)
            └── 读取 META-INF/spring.factories → 加载自动配置类
                 └── @ConditionalOnClass / @ConditionalOnMissingBean 条件筛选
```

### Starter 机制
- 约定大于配置：引入 `spring-boot-starter-web` 自动装配 Tomcat + SpringMVC
- 自定义 Starter：`xxx-spring-boot-autoconfigure` + `xxx-spring-boot-starter`

### 常见面试题
1. **Spring Boot 如何排除自动配置？** `@EnableAutoConfiguration(exclude=...)` 或配置 `spring.autoconfigure.exclude`
2. **Spring Boot 启动过程？** 创建 SpringApplication → 准备环境 → 创建 ApplicationContext → 刷新容器 → 执行 Runner

## 4. Spring MVC 请求处理流程

```
DispatcherServlet → HandlerMapping（找 Controller）
→ HandlerAdapter（执行）
→ Controller（处理请求）
→ ViewResolver（解析视图）
→ 响应
```

### 常见面试题
1. **拦截器 (Interceptor) 和过滤器 (Filter) 区别？** Filter 是 Servlet 规范，在 DispatcherServlet 之前，Interceptor 是 Spring 的，可访问 Spring 上下文
