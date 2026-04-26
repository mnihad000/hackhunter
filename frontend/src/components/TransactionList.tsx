import { formatCurrency, type Transaction } from "../demoLogic";

type TransactionListProps = {
  transactions: Transaction[];
  selectedCategory: string | null;
  onClearCategory: () => void;
};

function TransactionList({
  transactions,
  selectedCategory,
  onClearCategory,
}: TransactionListProps) {
  const emptyCopy = selectedCategory
    ? "No transactions in this category yet."
    : "No bank transactions yet. Connect a Plaid sandbox account to populate the workspace.";

  return (
    <section className="panel transaction-card" aria-labelledby="transactions-title">
      <div className="card-title-row">
        <div>
          <p className="section-label">{selectedCategory ? "filtered recent" : "recent"}</p>
          <h2 id="transactions-title">
            {selectedCategory ? selectedCategory : "Transactions"}
          </h2>
        </div>
        {selectedCategory && (
          <button className="text-action" type="button" onClick={onClearCategory}>
            Clear
          </button>
        )}
      </div>
      <ul className="transaction-list">
        {transactions.map((transaction) => (
          <li key={transaction.id}>
            <div>
              <strong>{transaction.merchant}</strong>
              <span>
                {transaction.category} - {transaction.time}
              </span>
            </div>
            <b>{formatCurrency(transaction.amount)}</b>
          </li>
        ))}
      </ul>
      {transactions.length === 0 && <p className="empty-copy">{emptyCopy}</p>}
    </section>
  );
}

export default TransactionList;
