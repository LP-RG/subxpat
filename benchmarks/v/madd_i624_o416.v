module madd_i624_o416 (a, b, c, r);
input [207:0] a,b,c;
output [415:0] r;

assign r = (a * b) + c;

endmodule
