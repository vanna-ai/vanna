// Mock data for Urban Eats Restaurant Chain Analytics

export interface RestaurantData {
  name: string;
  revenue: string;
  orders: number;
  avgTicket: string;
  topItem: string;
}

export interface MenuItem {
  name: string;
  category: string;
  sales: number;
  revenue: string;
}

export interface MonthlyRevenue {
  month: string;
  revenue: number;
  orders: number;
}

export interface LocationComparison {
  metric: string;
  downtown: string;
  airport: string;
  difference: string;
}

export const topRestaurants: RestaurantData[] = [
  { name: "Downtown", revenue: "$1.2M", orders: 15234, avgTicket: "$78.80", topItem: "Burger" },
  { name: "Airport", revenue: "$980K", orders: 12456, avgTicket: "$78.67", topItem: "Salad" },
  { name: "Marina Bay", revenue: "$875K", orders: 11203, avgTicket: "$78.12", topItem: "Pizza" },
  { name: "Westside", revenue: "$762K", orders: 9876, avgTicket: "$77.15", topItem: "Pasta" },
  { name: "East Village", revenue: "$698K", orders: 9234, avgTicket: "$75.60", topItem: "Burger" },
];

export const topMenuItems: MenuItem[] = [
  { name: "Classic Burger", category: "Burgers", sales: 23456, revenue: "$328K" },
  { name: "Caesar Salad", category: "Salads", sales: 18234, revenue: "$255K" },
  { name: "Margherita Pizza", category: "Pizza", sales: 16789, revenue: "$268K" },
  { name: "Grilled Salmon", category: "Seafood", sales: 14567, revenue: "$365K" },
  { name: "Pasta Carbonara", category: "Pasta", sales: 13456, revenue: "$215K" },
  { name: "Chicken Wings", category: "Appetizers", sales: 12345, revenue: "$148K" },
  { name: "BBQ Ribs", category: "Mains", sales: 11234, revenue: "$314K" },
  { name: "Veggie Wrap", category: "Wraps", sales: 10987, revenue: "$142K" },
  { name: "Fish Tacos", category: "Mexican", sales: 9876, revenue: "$158K" },
  { name: "Chocolate Cake", category: "Desserts", sales: 9234, revenue: "$111K" },
];

export const revenueByMonth: MonthlyRevenue[] = [
  { month: "Jul", revenue: 2350000, orders: 42150 },
  { month: "Aug", revenue: 2420000, orders: 43800 },
  { month: "Sep", revenue: 2510000, orders: 45200 },
  { month: "Oct", revenue: 2680000, orders: 47300 },
  { month: "Nov", revenue: 2890000, orders: 50100 },
  { month: "Dec", revenue: 2730000, orders: 48521 },
];

export const locationComparisonData: LocationComparison[] = [
  { metric: "Revenue", downtown: "$1.2M", airport: "$980K", difference: "+22%" },
  { metric: "Orders", downtown: "15,234", airport: "12,456", difference: "+22%" },
  { metric: "Avg Ticket", downtown: "$78.80", airport: "$78.67", difference: "+0.2%" },
  { metric: "Top Item", downtown: "Burger", airport: "Salad", difference: "-" },
];

export const weekdayVsWeekend = [
  { day: "Mon", weekday: 380000, weekend: 0 },
  { day: "Tue", weekday: 375000, weekend: 0 },
  { day: "Wed", weekday: 390000, weekend: 0 },
  { day: "Thu", weekday: 405000, weekend: 0 },
  { day: "Fri", weekday: 450000, weekend: 0 },
  { day: "Sat", weekday: 0, weekend: 520000 },
  { day: "Sun", weekday: 0, weekend: 485000 },
];

export interface SuggestedQuestion {
  label: string;
  question: string;
}

export const suggestedQuestions: SuggestedQuestion[] = [
  { label: "Top 5 Restaurants", question: "Show me top 5 restaurants by revenue" },
  { label: "Best Selling Items", question: "What are our best selling menu items?" },
  { label: "Weekend Sales", question: "Compare weekday vs weekend sales" },
  { label: "Revenue Trend", question: "Show revenue trend for last 6 months" },
  { label: "Location Comparison", question: "Compare Downtown and Airport locations" },
  { label: "Monthly Performance", question: "How are we doing this month?" },
];

// Message type for mock responses
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: {
    type: "table" | "chart" | "card" | "buttons";
    payload?: any;
  };
}

/**
 * Generate mock response for offline demos
 */
export function generateMockResponse(question: string): Message {
  const lowerQuestion = question.toLowerCase();

  // Top 5 restaurants
  if (lowerQuestion.includes("top") && (lowerQuestion.includes("restaurant") || lowerQuestion.includes("location"))) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here are your top performing locations by revenue:",
      data: {
        type: "table",
        payload: topRestaurants,
      },
    };
  }

  // Best selling items
  if (lowerQuestion.includes("best") || (lowerQuestion.includes("top") && lowerQuestion.includes("item"))) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here are your best selling menu items across all locations:",
      data: {
        type: "table",
        payload: topMenuItems,
      },
    };
  }

  // Revenue trend
  if (lowerQuestion.includes("revenue") && (lowerQuestion.includes("trend") || lowerQuestion.includes("month") || lowerQuestion.includes("6"))) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here's the revenue trend for Urban Eats over the last 6 months. You can see steady growth of 3-5% month over month, with a peak in November likely due to holiday events.",
      data: {
        type: "chart",
        payload: {
          type: "area",
          data: revenueByMonth,
          dataKeys: [{ key: "revenue", name: "Revenue", color: "hsl(217, 91%, 60%)" }],
          xAxisKey: "month",
          title: "Revenue Trend - Last 6 Months",
        },
      },
    };
  }

  // Location comparison
  if (lowerQuestion.includes("compare") && (lowerQuestion.includes("downtown") || lowerQuestion.includes("airport"))) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here's how Downtown and Airport compare:\n\nDowntown outperforms Airport by 22% in revenue, though average ticket size is nearly identical.",
      data: {
        type: "table",
        payload: locationComparisonData,
      },
    };
  }

  // Weekday vs Weekend
  if (lowerQuestion.includes("weekday") || lowerQuestion.includes("weekend")) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here's the comparison between weekday and weekend sales. Weekend sales show significantly higher revenue, with Saturday being the peak day.",
      data: {
        type: "chart",
        payload: {
          type: "bar",
          data: weekdayVsWeekend,
          dataKeys: [
            { key: "weekday", name: "Weekday", color: "hsl(217, 91%, 60%)" },
            { key: "weekend", name: "Weekend", color: "hsl(200, 80%, 50%)" },
          ],
          xAxisKey: "day",
          title: "Weekday vs Weekend Sales",
        },
      },
    };
  }

  // Monthly performance
  if (lowerQuestion.includes("month") || lowerQuestion.includes("doing")) {
    return {
      id: Date.now().toString(),
      role: "assistant",
      content: "Here's your monthly performance summary for Urban Eats:",
      data: {
        type: "card",
        payload: {
          title: "December 2024 Performance",
          trend: "↑ 8.3% vs last month",
          stats: [
            { label: "Total Revenue", value: "$2.73M" },
            { label: "Total Orders", value: "48,521" },
            { label: "Avg Order Value", value: "$56.28" },
            { label: "Active Locations", value: "25" },
          ],
        },
      },
    };
  }

  // Default response
  return {
    id: Date.now().toString(),
    role: "assistant",
    content: "I can help you analyze your restaurant data. Try asking about:\n\n• Top performing locations\n• Best selling menu items\n• Revenue trends\n• Location comparisons\n• Sales patterns\n\nWhat would you like to know?",
  };
}
