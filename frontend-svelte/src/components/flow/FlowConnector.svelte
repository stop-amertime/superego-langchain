<script lang="ts">
  // Connector for visualizing flow between nodes
  export let length = 40; // Default height of connector in pixels
</script>

<div class="connector" style="height: {length}px;">
  <div class="line"></div>
  <div class="arrow"></div>
</div>

<style>
  .connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    width: 100%;
  }
  
  .line {
    width: 2px;
    background-color: #ccc;
    flex-grow: 1;
  }
  
  .arrow {
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #ccc;
    margin-top: -1px;
  }
</style>
