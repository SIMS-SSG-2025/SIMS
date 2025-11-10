
<script lang="ts">
		import { X } from 'lucide-svelte';
		import type { Snippet } from 'svelte';

		let {
			open = $bindable(false),
			onClose = () => {},
			modalClass = "",
			children
		}: {
			open: boolean;
			onClose: () => void;
			modalClass?: string;
			children: Snippet;
		} = $props();
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-center justify-center">
		<!-- Blurred background -->
		<div
			class="absolute inset-0 backdrop-blur-sm bg-black/20"
			role="button"
			tabindex="0"
			aria-label="Close modal background"
			onclick={onClose}
			onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onClose(); } }}
		></div>
		<!-- Modal content -->
		<div class={`relative bg-white rounded-2xl shadow-2xl z-10 border border-gray-200 flex flex-col items-center overflow-hidden ${modalClass}`}>
			<button
				class="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 text-gray-500 z-10"
				onclick={onClose}
				aria-label="Close"
			>
				<X class="h-6 w-6" />
			</button>
			{@render children()}
		</div>
	</div>
{/if}
