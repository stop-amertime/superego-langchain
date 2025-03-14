<script>
  // This is a simple component that renders a vertical line connecting agent cards
</script>

<div class="connection-line" aria-hidden="true">
  <div class="line"></div>
  <div class="arrow"></div>
</div>

<style>
  .connection-line {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 20px;
    margin: -8px 0;
    position: relative;
  }
  
  .line {
    width: 2px;
    height: 100%;
    background-color: #ddd;
  }
  
  .arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #ddd;
    position: absolute;
    bottom: -1px;
  }
</style>
