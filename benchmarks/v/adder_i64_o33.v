module adder_i64_o33(a,b,r);
input [31:0] a,b;
output [33:0] r;

assign r = a+b;

endmodule
