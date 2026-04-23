module madd_i23040_o15360 (a, b, c, r);
input [7679:0] a,b,c;
output [15359:0] r;

assign r = (a * b) + c;

endmodule
