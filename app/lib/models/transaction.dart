enum TxnType { deposit, withdraw, goal }

class Txn {
  final int id;
  final TxnType type;
  final String desc;
  final String sub;
  final int? amount;
  final String date;

  const Txn({
    required this.id,
    required this.type,
    required this.desc,
    required this.sub,
    this.amount,
    required this.date,
  });
}

final List<Txn> sampleTxns = [
  const Txn(
    id: 1,
    type: TxnType.deposit,
    desc: 'Money Added',
    sub: 'From HDFC Bank •••• 1234',
    amount: 5000,
    date: '28 May, 2025',
  ),
  const Txn(
    id: 2,
    type: TxnType.goal,
    desc: 'Goal Created',
    sub: 'iPhone 16 Pro',
    amount: null,
    date: '26 May, 2025',
  ),
  const Txn(
    id: 3,
    type: TxnType.withdraw,
    desc: 'Emergency Withdrawal',
    sub: 'From Goa Trip',
    amount: -2000,
    date: '24 May, 2025',
  ),
  const Txn(
    id: 4,
    type: TxnType.deposit,
    desc: 'Money Added',
    sub: 'From ICICI Bank •••• 5678',
    amount: 3000,
    date: '22 May, 2025',
  ),
  const Txn(
    id: 5,
    type: TxnType.deposit,
    desc: 'Auto Deposit',
    sub: 'SIP — Royal Enfield',
    amount: 2500,
    date: '21 May, 2025',
  ),
];
