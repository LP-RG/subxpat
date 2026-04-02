module madd_i177_o118 (a, b, c, r);
input [58:0] a,b,c;
output [117:0] r;

assign r = (a * b) + c;

endmodule
