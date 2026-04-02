module adder_i1024_o513(a,b,r);
input [511:0] a,b;
output [512:0] r;

assign r = a+b;

endmodule
