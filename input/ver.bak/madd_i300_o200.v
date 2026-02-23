module madd_i300_o200 (a, b, c, r);
input [99:0] a,b,c;
output [199:0] r;

assign r = (a * b) + c;

endmodule
