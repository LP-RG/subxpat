module madd_i168_o112 (a, b, c, r);
input [55:0] a,b,c;
output [111:0] r;

assign r = (a * b) + c;

endmodule
