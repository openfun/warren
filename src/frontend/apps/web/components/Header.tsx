import styles from "./Header.module.scss";

export default () => (
  <header className={styles.core}>
    <a href="/" title="Home">
      <h1>
        Warren{" "}
        <span>The visualization toolkit for your learning analytics</span>
      </h1>
    </a>
  </header>
);
