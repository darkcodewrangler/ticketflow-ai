interface TodoStatsProps {
  total: number;
  completed: number;
  remaining: number;
}

const TodoStats = ({ total, completed, remaining }: TodoStatsProps) => {
  return (
    <div className="flex justify-center gap-6 mb-6 text-sm text-gray-600">
      <span>Total: {total}</span>
      <span>Completed: {completed}</span>
      <span>Remaining: {remaining}</span>
    </div>
  );
};

export default TodoStats;