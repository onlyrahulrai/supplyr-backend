TRANSLATABLES = [
    "quantity",
    "order_number_prefix"
]

ORDER_STATUS_OPTIONS = [
    {
        "slug":"awaiting_approval",
        "name":"Awaiting Approval",
        "sequence":1,
        "transitions_possible":["approved","cancelled"],
        "editing_allowed":True,
    },
    {
        "slug":"approved",
        "name":"Approved",
        "sequence":2,
        "transitions_possible":["processed","cancelled"],
        "editing_allowed":True,
    },
    {
        "slug":"processed",
        "name":"Processed",
        "sequence":3,
        "transitions_possible":["dispatched","approved","cancelled"],
        "editing_allowed":False,
    },
    {
        "slug":"dispatched",
        "name":"Dispatched",
        "sequence":4,
        "transitions_possible":["delivered","returned","cancelled"],
        "editing_allowed":False,
    },
    {
        "slug":"returned",
        "name":"Returned",
        "sequence":5,
        "transitions_possible":['processed', 'cancelled'],
        "editing_allowed":True,
        "confirmation_needed":True
    },
    {
        "slug":"delivered",
        "name":"Delivered",
        "sequence":6,
        "transitions_possible":[],
        "editing_allowed":False,
    },
    {
        "slug":"cancelled",
        "name":"Cancelled",
        "sequence":7,
        "transitions_possible":['approved',],
        "editing_allowed":False,
        "confirmation_needed":True
    },
]

ADD_LEDGER_ENTRY_ON_MARK_ORDER_PAID = True