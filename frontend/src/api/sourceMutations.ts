import { useQueryClient } from "@tanstack/react-query"

import { sourcesApi } from "./client"

const LIST_KEY = ["get", "/"]

/** Every mutation refetches the list, so the table never shows a stale row. */
function useListInvalidation() {
  const queryClient = useQueryClient()

  return {
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: LIST_KEY })
    },
  }
}

export function useSources() {
  return sourcesApi.useQuery("get", "/")
}

export function useCreateSource() {
  return sourcesApi.useMutation("post", "/", useListInvalidation())
}

export function useUpdateSource() {
  return sourcesApi.useMutation("patch", "/{source_id}", useListInvalidation())
}

export function useDeleteSource() {
  return sourcesApi.useMutation("delete", "/{source_id}", useListInvalidation())
}
