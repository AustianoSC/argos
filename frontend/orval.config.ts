import { defineConfig } from "orval";

export default defineConfig({
  argos: {
    input: {
      target: "./src/api/openapi.json",
    },
    output: {
      target: "./src/api/backend.ts",
      client: "react-query",
      httpClient: "fetch",
      baseUrl: "",
      override: {
        mutator: {
          path: "./src/api/fetch.ts",
          name: "customFetch",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
