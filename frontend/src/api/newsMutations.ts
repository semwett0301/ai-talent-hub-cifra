import { useQueryClient } from "@tanstack/react-query"

import { newsApi } from "./client"
import type { NewsListParams } from "./news"

// openapi-react-query keys are [method, path, init]; this prefix covers every page of
// the news list (the sources list shares the shape and refetches too — harmless).
const LIST_KEY = ["get", "/"]

/** Every mutation refetches the list, so a hidden item leaves the feed at once. */
function useListInvalidation() {
  const queryClient = useQueryClient()

  return {
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: LIST_KEY })
    },
  }
}

export function useNews(params: NewsListParams) {
  return newsApi.useQuery("get", "/", { params: { query: params } })
}

export function useDismissNews() {
  return newsApi.useMutation("post", "/{news_id}/dismiss", useListInvalidation())
}

export function useRestoreNews() {
  return newsApi.useMutation("post", "/{news_id}/restore", useListInvalidation())
}
