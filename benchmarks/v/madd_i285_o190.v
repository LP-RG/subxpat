module madd_i285_o190 (a, b, c, r);
input [94:0] a,b,c;
output [189:0] r;

assign r = (a * b) + c;

endmodule
