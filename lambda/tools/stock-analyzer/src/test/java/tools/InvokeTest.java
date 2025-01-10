package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.amazonaws.services.lambda.runtime.Context;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import tools.StockAnalyzerLambda.ToolEvent;
import tools.StockAnalyzerLambda.ToolInput;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class InvokeTest {
  private static final Logger logger = LoggerFactory.getLogger(InvokeTest.class);

  private StockAnalyzerLambda handler;
  private static final double DELTA = 0.0001; // For double comparisons

  @BeforeEach
  void setUp() {
    handler = new StockAnalyzerLambda();
  }

  @Test
  void testMovingAverageCalculation() throws Exception {
    // Create test event for moving average
    StockAnalyzerLambda.ToolEvent event = new StockAnalyzerLambda.ToolEvent();
    event.setId("test-id");
    event.setName("calculate_moving_average");

    // Create sample data
    String sampleCsv = "AAPL,100.0,102.0,104.0,103.0,105.0,106.0,107.0\n" +
        "GOOGL,2800.0,2820.0,2840.0,2830.0,2860.0,2880.0,2900.0";

    // Mock S3 read by overriding readStockDataFromS3
    StockAnalyzerLambda testHandler = new StockAnalyzerLambda() {
      @Override
      protected Map<String, List<Double>> readStockDataFromS3(String bucket, String key) {
        Map<String, List<Double>> data = new HashMap<>();
        data.put("AAPL", Arrays.asList(100.0, 102.0, 104.0, 103.0, 105.0, 106.0, 107.0));
        data.put("GOOGL", Arrays.asList(2800.0, 2820.0, 2840.0, 2830.0, 2860.0, 2880.0, 2900.0));
        return data;
      }
    };

    // Create input
    StockAnalyzerLambda.ToolInput input = new StockAnalyzerLambda.ToolInput();
    input.setBucket("test-bucket");
    input.setKey("test-key");
    event.setInput(input);

    // Get response
    Map<String, String> response = testHandler.handleRequest(event, null);

    // Parse the JSON response
    ObjectMapper mapper = new ObjectMapper();
    Map<String, List<Double>> result = mapper.readValue(response.get("content"),
        new TypeReference<Map<String, List<Double>>>() {
        });

    // Verify results
    assertNotNull(result);
    assertTrue(result.containsKey("AAPL"));
    assertTrue(result.containsKey("GOOGL"));

    List<Double> aaplMA = result.get("AAPL");
    // Calculate expected 3-day moving average manually for verification
    assertEquals(Double.NaN, aaplMA.get(0));
    assertEquals(Double.NaN, aaplMA.get(1));
    assertEquals((100.0 + 102.0 + 104.0) / 3, aaplMA.get(2), DELTA);
    assertEquals((102.0 + 104.0 + 103.0) / 3, aaplMA.get(3), DELTA);
  }

  @Test
  void testVolatilityCalculation() throws Exception {
    StockAnalyzerLambda.ToolEvent event = new StockAnalyzerLambda.ToolEvent();
    event.setId("test-id");
    event.setName("calculate_volatility");

    // Create a handler with known test data
    StockAnalyzerLambda testHandler = new StockAnalyzerLambda() {
      @Override
      protected Map<String, List<Double>> readStockDataFromS3(String bucket, String key) {
        Map<String, List<Double>> data = new HashMap<>();
        // Using simple price series with known volatility
        data.put("AAPL", Arrays.asList(100.0, 101.0, 100.0, 102.0, 101.0));
        return data;
      }
    };

    StockAnalyzerLambda.ToolInput input = new StockAnalyzerLambda.ToolInput();
    input.setBucket("test-bucket");
    input.setKey("test-key");
    event.setInput(input);

    Map<String, String> response = testHandler.handleRequest(event, null);

    // Parse the JSON response
    ObjectMapper mapper = new ObjectMapper();
    Map<String, Double> result = mapper.readValue(response.get("content"),
        new TypeReference<Map<String, Double>>() {
        });

    assertNotNull(result);
    assertTrue(result.containsKey("AAPL"));
    assertTrue(result.get("AAPL") > 0); // Volatility should be positive
  }

  @Test
  void testSimpleMovingAverage() {
    // Test the moving average calculation directly
    List<Double> prices = Arrays.asList(100.0, 102.0, 104.0, 103.0, 105.0);
    StockAnalyzerLambda.MovingAverageTask task = new StockAnalyzerLambda.MovingAverageTask(prices, 0, prices.size(), 3);

    List<Double> result = task.compute();

    // First two values should be NaN (not enough data for 3-day MA)
    assertTrue(Double.isNaN(result.get(0)));
    assertTrue(Double.isNaN(result.get(1)));

    // Verify remaining values
    assertEquals((100.0 + 102.0 + 104.0) / 3, result.get(2), DELTA);
    assertEquals((102.0 + 104.0 + 103.0) / 3, result.get(3), DELTA);
    assertEquals((104.0 + 103.0 + 105.0) / 3, result.get(4), DELTA);
  }

  @Test
  void testHistoricalVolatility() {
    // Create a simple price series with known volatility
    List<Double> prices = Arrays.asList(100.0, 101.0, 100.0, 102.0, 101.0);

    // Calculate returns manually
    List<Double> returns = new ArrayList<>();
    for (int i = 1; i < prices.size(); i++) {
      returns.add(Math.log(prices.get(i) / prices.get(i - 1)));
    }

    double mean = returns.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
    double variance = returns.stream()
        .mapToDouble(r -> Math.pow(r - mean, 2))
        .average().orElse(0.0);
    double expectedVolatility = Math.sqrt(variance * 252) * 100;

    // Test the volatility calculation
    StockAnalyzerLambda testHandler = new StockAnalyzerLambda();
    double calculatedVolatility = testHandler.calculateHistoricalVolatility(prices);

    assertEquals(expectedVolatility, calculatedVolatility, DELTA);
  }

  @Test
  void testVolatilityCalculationDetailed() {
    // Create a simple price series with known changes
    List<Double> prices = Arrays.asList(100.0, 101.0, 100.0, 102.0, 101.0);

    System.out.println("Input prices: " + prices);

    // Calculate returns and print each step
    List<Double> returns = new ArrayList<>();
    for (int i = 1; i < prices.size(); i++) {
      double returnValue = Math.log(prices.get(i) / prices.get(i - 1));
      returns.add(returnValue);
      System.out.printf("Day %d return: %.6f (Price: %.2f / %.2f)%n",
          i, returnValue, prices.get(i), prices.get(i - 1));
    }

    // Calculate mean
    double mean = returns.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
    System.out.printf("Mean of returns: %.6f%n", mean);

    // Calculate variance
    double variance = returns.stream()
        .mapToDouble(r -> Math.pow(r - mean, 2))
        .average().orElse(0.0);
    System.out.printf("Variance of returns: %.6f%n", variance);

    // Calculate annualized volatility
    double volatility = Math.sqrt(variance * 252) * 100;
    System.out.printf("Annualized volatility: %.2f%%%n", volatility);

    StockAnalyzerLambda handler = new StockAnalyzerLambda();
    double calculatedVolatility = handler.calculateHistoricalVolatility(prices);
    System.out.printf("Function calculated volatility: %.2f%%%n", calculatedVolatility);

    assertFalse(Double.isNaN(calculatedVolatility), "Volatility should not be NaN");
    assertEquals(volatility, calculatedVolatility, 0.0001);
  }


  @Test
  void testHandlerS3Data() throws Exception {
    logger.info("Invoke TEST - HandlerMovingAverage");
    ToolEvent inputData = new ToolEvent();
    inputData.setId("toolu_01GzN3ATS4f3UZAgeV57UCC9");
    inputData.setName("calculate_moving_average");
    ToolInput input = new ToolInput();
    input.setBucket("blah-bucket");
    input.setKey("stock_data.csv");
    inputData.setInput(input);
    Context context = new TestContext();
    Map<String, String> outputData = handler.handleRequest(inputData, context);

    // Serialize to JSON string
    ObjectMapper mapper = new ObjectMapper();
    String jsonOutput = mapper.writeValueAsString(outputData);

    // Print the actual JSON for debugging
    System.out.println("Generated JSON from real call: " + jsonOutput);

    assertNotNull(outputData.get("tool_use_id"));
    assertNotNull(outputData.get("content"));
    assertEquals("tool_result", outputData.get("type"));
  }
}