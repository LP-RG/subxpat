module madd_i312_o208 (a, b, c, r);
input [103:0] a,b,c;
output [207:0] r;

assign r = (a * b) + c;

endmodule
