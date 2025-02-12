import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Extreme Flexibility',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        AI Agents Framework allows you to call any LLM and use any tool in any programming language.
      </>
    ),
  },
  {
    title: 'Extreme Observability',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Built on top of the reliable serverless infrastructure (AWS Lambda and Step Functions), AI Agents Framework provides extreme observability.
        Inspect every execution step and every tool call, using CloudWatch and X-ray.
      </>
    ),
  },
  {
    title: 'Extreme Scalability',
    Svg: require('@site/static/img/scalability.svg').default,
    description: (
      <>
        Based on true serverless architecture, AI Agents Framework can scale to any number of concurrent users and any number of concurrent executions.
        You only pay for what you use.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
