
<script lang="ts">
		export let open: boolean = false;
		export let onClose: () => void = () => {};
		export let modalClass: string = "";
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-center justify-center">
		<!-- Blurred background -->
		<div class="absolute inset-0 backdrop-blur-sm bg-black/20" on:click={onClose}></div>
		<!-- Modal content -->
		<div class={`relative bg-white rounded-2xl shadow-2xl z-10 border border-gray-200 flex flex-col items-center ${modalClass}`}>
			<button
				class="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 text-gray-500"
				on:click={onClose}
				aria-label="Close"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
			<slot />
		</div>
	</div>
{/if}
