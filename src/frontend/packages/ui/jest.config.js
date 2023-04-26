module.exports = {
  roots: ["."],
  preset: 'ts-jest',

  // Jest transformations -- this adds support for TypeScript
  // using ts-jest
  transform: {
    "^.+\\.tsx?$": ["ts-jest", {    
          isolatedModules: true
    }]
  },

  testRegex: "(/__tests__/.*|(\\.|/)(test|spec))\\.tsx?$",

  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],
  testEnvironment: 'node',


};
