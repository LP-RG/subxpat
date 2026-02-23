module madd_i105_o70 (a, b, c, r);
input [34:0] a,b,c;
output [69:0] r;

assign r = (a * b) + c;

endmodule
