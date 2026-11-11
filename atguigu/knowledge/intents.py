from dataclasses import dataclass, field


# 创建类，存储知识检索
@dataclass
class KnowledgeIntent:
    id: str  # 范围值，提交llm，意图识别返回结果
    description: str  # id范围值中文描述，提交llm
    # 答案位置
    provider_ids: list[str]=field(default_factory=list)
    requires_object: str | None = None

# 创建字典，定义知识检索范围
KNOWLEDGE_INTENTS:dict[str, KnowledgeIntent] = {
    "product_info": KnowledgeIntent(
        id="product_info",description="商品信息咨询",
        provider_ids=["api.product"], requires_object="product",
    ),
    "order_info": KnowledgeIntent(
        id="order_info", description="订单信息咨询",
        provider_ids=["api.order"], requires_object="order",
    ),

    "refund_policy": KnowledgeIntent(
        id="refund_policy", description="退款政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "return_policy": KnowledgeIntent(
        id="return_policy", description="退货政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "shipping_policy": KnowledgeIntent(
        id="shipping_policy", description="配送政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "platform_rule": KnowledgeIntent(
        id="platform_rule", description="平台规则咨询",
        provider_ids=["rag.default"],
    ),
    "general_ecommerce_info": KnowledgeIntent(
        id="general_ecommerce_info", description="电商通用信息咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
}

# ============================================================================
# 本文件的作用：定义“系统支持哪些知识咨询，以及每类咨询应该去哪里找答案”。
#
# 一、用“秦志颖去医院咨询”来理解
# 这份文件相当于咨询台的“咨询事项目录”：
#   查询个人报告 → 去报告查询窗口，需要提供具体的就诊信息。
#   询问医院退费规则 → 查规则手册，不一定需要指定某个人的就诊信息。
# 对应到当前电商项目：
#   商品信息咨询 → api.product，需要明确正在咨询哪个商品。
#   退款政策咨询 → faq.default、rag.default，配置中不要求指定订单或商品。
# 这里保存的是咨询分类和答案来源的标识，并没有保存具体答案。
#
# 二、KnowledgeIntent：一条咨询事项的配置
# id：机器使用的意图标识，例如 refund_policy，供规划结果引用。
# description：给人和大模型理解的描述，例如“退款政策咨询”。
# provider_ids：答案提供者的标识列表；这些字符串不是接口地址，也不是查询结果。
#   api.product / api.order：表示商品、订单信息来源。
#   faq.default / rag.default：表示常见问题、检索增强知识来源。
#   如何找到并调用这些提供者，以及多个来源怎样组合，由后续处理代码实现。
# requires_object：该咨询需要哪种业务对象，例如 product 或 order。
#   它记录的是对象类型，不是具体商品号或订单号；None 表示此配置不要求对象。
#   该字段只是声明要求，不会自动检查对象是否存在，也不会自动向用户追问。
# field(default_factory=list)：每个未传 provider_ids 的实例各自创建一个空列表，
#   避免多个实例共用同一个可变列表。
#
# 三、KNOWLEDGE_INTENTS：把所有咨询事项按 id 放在一起，方便查找
# 例如：intent = KNOWLEDGE_INTENTS['refund_policy']
# 得到的是一个 KnowledgeIntent 对象，可以读取 intent.provider_ids 等属性。
# 它与 FlowCatalog 的区别：FlowCatalog 管“业务流程怎么一步步执行”；
# 这里管“知识问题有哪些类别、需要什么对象、配置了哪些答案来源”。
#
# 四、预期在整个项目中的位置
# 用户提问 → Planner 结合咨询目录识别意图 → TurnPlan.knowledge.intents
#          → 校验意图和所需对象 → 按 provider_ids 获取知识 → 组织回复。
# 例如“退款有哪些条件？”可以识别为 refund_policy，
# 后续根据这份配置选择 faq.default、rag.default 获取相关内容。
#
# 五、当前接入情况（添加本说明时）
# turn_planner.py 传给提示词的 knowledge_intents_json 仍是空字典，
# dialogue_engine.py 的 knowledge 分支仍返回空列表并标记 TODO。
# 因此，本文件目前定义了配置，但还没有接通上述知识问答链路。
# 仅定义这些类和字典，不会自动调用大模型、查询接口或执行知识检索。
# ============================================================================
