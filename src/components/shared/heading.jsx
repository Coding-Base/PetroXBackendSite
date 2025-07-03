export default function Heading({ title, description, className }) {
  return (
    <div className={className}>
      <h2 className="text-primary text-xl font-bold tracking-tight sm:text-3xl">
        {title}
      </h2>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}
