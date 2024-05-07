interface BoundaryScreenErrorProps {
  message: string;
}

export const BoundaryScreenError = ({ message }: BoundaryScreenErrorProps) => {
  return (
    <div className="c__error">
      <div className="c__error__title">Whoops, something went wrong.</div>
      <div className="c__error__message">{message}</div>
    </div>
  );
};
